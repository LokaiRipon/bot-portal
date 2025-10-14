# selenium_setup.py
"""Handles Selenium WebDriver setup and connection."""
# TODO: Do not edit anything in this file
import requests
import zipfile
import io
import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

def get_full_chrome_version(debugger_address):
    """
    Queries the DevTools JSON endpoint to get the full Chrome version,
    e.g. "131.0.6778.76"
    """
    try:
        resp = requests.get(f"http://{debugger_address}/json/version", timeout=5).json()
        browser = resp.get("Browser", "")
        return browser.split("/", 1)[1] if "/" in browser else None
    except Exception as e:
        print(f"[DEBUG] Failed to detect Chrome version: {e}")
        return None

def ensure_exact_chromedriver(chrome_version, status_label=None): # Add status_label parameter
    major = chrome_version.split(".")[0]
    # --- FIX: Remove trailing space ---
    meta_url = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json"
    # -------------------------------
    if status_label:
        status_label.config(text=f"Checking ChromeDriver for Chrome {major}...")
        status_label.update_idletasks()
    manifest = requests.get(meta_url).json()
    entry = manifest["milestones"].get(major)
    if not entry:
        raise RuntimeError(f"No ChromeDriver for Chrome major version {major}")
    sys_name = platform.system().lower()
    if sys_name == "windows":
        target_plat = "win64"
    elif sys_name == "darwin":
        target_plat = "mac-x64"
    else:
        target_plat = "linux64"
    asset = next(
        (a for a in entry["downloads"]["chromedriver"] if a["platform"] == target_plat),
        None
    )
    if not asset:
        raise RuntimeError(f"No chromedriver download for platform {target_plat}")
    driver_version = entry["version"]
    download_url = asset["url"]
    out_dir = os.path.join(os.getcwd(), "drivers", driver_version)
    os.makedirs(out_dir, exist_ok=True)
    driver_exe = os.path.join(out_dir, "chromedriver.exe") # Adjust for other OS if needed
    if os.path.exists(driver_exe):
        if status_label:
            status_label.config(text=f"ChromeDriver {driver_version} already present.")
            status_label.update_idletasks()
        print(f"[DEBUG] ✔ ChromeDriver {driver_version} already present")
        return driver_exe
    # --- Simulate Download ---
    if status_label:
        status_label.config(text=f"Downloading ChromeDriver {driver_version}...")
        status_label.update_idletasks()
    # ------------------------
    print(f"[DEBUG] ↓ Downloading ChromeDriver {driver_version} for {target_plat}")
    resp = requests.get(download_url)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        for name in z.namelist():
            if name.endswith("chromedriver.exe"): # Adjust for other OS if needed
                z.extract(name, out_dir)
                os.rename(os.path.join(out_dir, name), driver_exe)
    # --- Simulate Save ---
    if status_label:
        status_label.config(text=f"ChromeDriver {driver_version} saved.")
        status_label.update_idletasks()
    # ---------------------
    print(f"[DEBUG] ✔ ChromeDriver {driver_version} saved to {driver_exe}")
    return driver_exe

def connect(status_label=None): # Add status_label parameter
    """
    Connect to Chrome via GOLOGIN API using standard Selenium.
    Does not add conflicting Chrome options.
    """
    from gologin_setup import get_gologin_browser
    if status_label:
        status_label.config(text="Starting GoLogin profile...")
        status_label.update_idletasks()
    print("🔄 [DEBUG] Starting connection process...")
    debugger_address = get_gologin_browser()
    if not debugger_address:
        print("❌ [DEBUG] Failed to get browser from GOLOGIN API")
        if status_label:
            status_label.config(text="Failed to start GoLogin profile.")
            status_label.update_idletasks()
        return None

    print(f"🔧 [DEBUG] Received debug address: {debugger_address}")

    if status_label:
        status_label.config(text="Detecting Chrome version...")
        status_label.update_idletasks()
    full_version = get_full_chrome_version(debugger_address)
    if not full_version:
        if status_label:
            status_label.config(text="Failed to detect Chrome version.")
            status_label.update_idletasks()
        return None

    try:
        chromedriver_path = ensure_exact_chromedriver(full_version, status_label) # Pass status_label
    except Exception as e:
        print(f"❌ [DEBUG] Failed to prepare ChromeDriver: {e}")
        if status_label:
            status_label.config(text=f"ChromeDriver setup failed: {e}")
            status_label.update_idletasks()
        return None

    try:
        if status_label:
            status_label.config(text="Connecting to browser...")
            status_label.update_idletasks()
        service = Service(executable_path=chromedriver_path)
        options = Options()
        options.debugger_address = debugger_address
        print(f"🔗 [DEBUG] Attempting to connect to {debugger_address}...")
        driver = webdriver.Chrome(service=service, options=options)

        # --- Add cleanup hook ---
        # original_quit = driver.quit # Store the original quit method
        # def new_quit():
        #     print("🔄 [DEBUG] Selenium driver.quit() called, stopping GoLogin profile...")
        #     from gologin_setup import stop_gologin_profile # Import inside the function to avoid circular issues
        #     original_quit() # Close the Selenium connection first
        #     stop_gologin_profile() # Then stop the GoLogin profile
        # driver.quit = new_quit # Replace the quit method
        # # ------------------------

        if driver:
            print("🎉 [DEBUG] SUCCESS: WebDriver object created")
            print(f"🌐 [DEBUG] Current URL: {driver.current_url}")
            print(f"📄 [DEBUG] Page Title: {driver.title}")
            print("✅ [DEBUG] Fully connected to GoLogin browser!")
            stealth_js = """
            delete navigator.__proto__.webdriver;
            """
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
            print("🛡️ [DEBUG] Minimal anti-bot stealth script injected.")
            if status_label:
                status_label.config(text="Connected! Browser is ready.")
                status_label.update_idletasks()
            return driver
    except Exception as e:
        print(f"💥 [DEBUG] FAILED to connect: {type(e).__name__} - {e}")
        if "session not created" in str(e).lower() and "version" in str(e).lower():
            print("   💡 ChromeDriver version mismatch. Ensure the correct binary is downloaded.")
        if status_label:
            status_label.config(text=f"Connection failed: {type(e).__name__}")
            status_label.update_idletasks()
        return None

# Note: The 'connect' function now handles stopping the profile when driver.quit() is called.
# This is achieved by replacing the driver.quit method.