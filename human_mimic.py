import pyautogui
import keyboard
import random
import time
import os

def clear_input_box():
    """Clears any existing text in the chat input box using Ctrl+A and Backspace."""
    try:
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.02)  # ultra-short pause
        pyautogui.press('backspace')
    except Exception as e:
        print(f"[DEBUG] Warning: Could not clear input box via hotkey: {e}")

def type_like_human(text):
    """
    Extreme-speed human-like typing.
    - Ultra-short delays overall (5–20ms per char)
    - Tiny punctuation pauses
    - Rare typos with instant correction
    - Occasional micro-pauses to keep rhythm natural
    """
    print("🔤 Typing:", text)
    i = 0
    chars_since_pause = 0

    while i < len(text):
        char = text[i]

        if keyboard.is_pressed('esc'):
            print("🛑 Typing cancelled by user (ESC pressed)")
            break

        pyautogui.write(char)

        # Rare typo injection (~1% chance)
        if random.random() < 0.01 and i < len(text) - 1 and char.isalpha():
            typo_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            pyautogui.write(typo_char)
            time.sleep(random.uniform(0.01, 0.02))  # blink-fast typo
            pyautogui.press('backspace')
            time.sleep(random.uniform(0.01, 0.02))  # blink-fast correction

        # Delay logic – ultra-tight
        if char in ['.', ',', '!', '?', ';', ':']:
            delay = random.uniform(0.02, 0.05)  # tiny punctuation pause
        else:
            delay = random.uniform(0.005, 0.02)  # ultra-fast base delay

        time.sleep(delay)
        i += 1
        chars_since_pause += 1

        # Micro-pause every 12–20 chars (very short)
        if chars_since_pause >= random.randint(12, 20):
            time.sleep(random.uniform(0.04, 0.08))  # subtle rhythm break
            chars_since_pause = 0

    print("✅ Typing complete")