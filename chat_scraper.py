# chat_scraper.py
"""Functions for scraping user profiles and chat history from the web page."""

# TODO: Dont touch the code in here!

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from bs4 import BeautifulSoup
from config import PROFILE_LEFT_SELECTOR, PROFILE_RIGHT_SELECTOR, CHAT_HISTORY_SELECTOR

def get_client_profile(driver):
    print(f"🔍 Attempting to get client profile using selector: '{PROFILE_LEFT_SELECTOR}'")
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"{PROFILE_LEFT_SELECTOR} .grid-item-name"))
        )
        elem = driver.find_element(By.CSS_SELECTOR, PROFILE_LEFT_SELECTOR)
        text = elem.text.strip()

        print(f"[DEBUG] Found client profile container. Text length: {len(text)}")
        if text:
            print("✅ Successfully fetched client profile data.")
            print(f"--- [DEBUG] RAW CLIENT PROFILE DATA ---\n{text}\n--- [DEBUG] END CLIENT PROFILE ---")
            return text
        else:
            print("⚠️ Client profile element found but empty.")
            return "Found class name but no text"

    except TimeoutException:
        print(f"❌ Timeout: Could not locate client profile element with selector '{PROFILE_LEFT_SELECTOR}' within 10s.")
        print(f"[DEBUG] Current Page URL: {driver.current_url}")
        print(f"[DEBUG] Current Page Title: {driver.title}")
        return "N/A No Client Pf"
    except Exception as e:
        print(f"❌ Can't get client profile: {type(e).__name__} - {e}")
        return "N/A No Client Pf"

def get_my_profile(driver):
    print(f"🔍 Attempting to get my profile using selector: '{PROFILE_RIGHT_SELECTOR}'")
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"{PROFILE_RIGHT_SELECTOR} .grid-item-name"))
        )
        elem = driver.find_element(By.CSS_SELECTOR, PROFILE_RIGHT_SELECTOR)
        text = elem.text.strip()

        print(f"[DEBUG] Found my profile container. Text length: {len(text)}")
        if text:
            print(f"👩 Your Profile:\n{text}")
            return text
        else:
            print("⚠️ My profile element found but empty.")
            return "Found class name but no text"

    except TimeoutException:
        print(f"❌ Timeout: Could not locate my profile element with selector '{PROFILE_RIGHT_SELECTOR}' within 10s.")
        print(f"[DEBUG] Current Page URL: {driver.current_url}")
        print(f"[DEBUG] Current Page Title: {driver.title}")
        return "Found class name but no text"
    except Exception as e:
        print(f"❌ Can't get your profile: {type(e).__name__} - {e}")
        return "Found class name but no text"

def extract_name_age(profile_text):
    """
    Extracts the first 'Name, Age' pattern from your profile text.
    Example: 'Miriam, 65' → ('Miriam', '65')
    """
    for line in profile_text.split("\n"):
        line = line.strip()
        if re.match(r"^[A-Za-z][A-Za-z\s]+,\s*\d{1,3}$", line):
            name, age = [p.strip() for p in line.split(",", 1)]
            return name, age
    return None, None

def extract_locality(profile_text):
    """
    Extracts the locality from a line like:
    'LOCALITY: Wheatland, Missouri'
    """
    for line in profile_text.split("\n"):
        if "locality:" in line.lower():
            return line.split(":", 1)[1].strip()
    return None

def get_chat_history(driver):
    """
    Get full chat history by extracting the INNER HTML of the container in one go.
    Parses it locally with BeautifulSoup to label messages as "Client:" or "You:" based on their class.
    Filters out system-generated messages like "FAVORITE" notifications.
    """
    print("🔍 Trying to get chat history (via innerHTML) classname...")
    try:
        chat_container = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, CHAT_HISTORY_SELECTOR))
        )
        print("✅ Found chat history container.")
        import time

        time.sleep(0.2)
        inner_html = chat_container.get_attribute('innerHTML')
        if not inner_html:
            print("❌ No inner HTML found within the chat container.")
            return "Client: Hello"

        print(f"📄 Extracted inner HTML (length: {len(inner_html)} chars).")

        soup = BeautifulSoup(inner_html, 'html.parser')

        labeled_messages = []

        all_messages = soup.find_all(class_=['message-customer', 'message-profile'])

        from typing import cast
        from bs4 import Tag
        
        for elem in all_messages:
            msg_elem = cast(Tag, elem)
            msg_text = msg_elem.get_text(separator=' ', strip=True)
            if not msg_text:
                continue
                
            raw_classes = msg_elem.get('class')
            classes = raw_classes if isinstance(raw_classes, list) else []
            print(f"[DEBUG] Classes for message: {classes!r}") 

            # --- NEW: Filter out system notifications ---
            msg_lower = msg_text.lower()
            system_keywords = [
                "added you to", "favorites", "favorite", "poke", "flirt", 
                "just wanted to let you know", "notification", "system", 
                "team", "moderator", "admin", "support", "alert"
            ]
            
            is_system_message = any(keyword in msg_lower for keyword in system_keywords)
            
            if is_system_message:
                print(f"[DEBUG] 🚫 Skipping system message: {msg_text[:60]}...")
                continue
            # --- END FILTER ---

            if 'message-customer' in classes:
                sender = "Client"
            elif 'message-profile' in classes:
                sender = "You"
            else:
                continue

            labeled_messages.append(f"{sender}: {msg_text}")

        if not labeled_messages:
            print("⚠️ No messages parsed from HTML.")
            return "Client: Hello"

        formatted_chat_history = "\n".join(labeled_messages)
        print(f"✅ Parsed {len(labeled_messages)} labeled messages.")

        return formatted_chat_history

    except TimeoutException:
        print(f"❌ Timeout: Could not locate chat container '{CHAT_HISTORY_SELECTOR}' within 15s.")
        print(f"[DEBUG] Current Page URL: {driver.current_url}")
        print(f"[DEBUG] Current Page Title: {driver.title}")
        return "Client: Hello"
    except Exception as e:
        print(f"❌ Unexpected error in get_chat_history: {type(e).__name__} - {e}")
        import traceback
        print(f"[DEBUG] Traceback:{traceback.format_exc()}")
        return "Client: Hello"