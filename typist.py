# typist.py
import time
import keyboard
from human_mimic import type_like_human, clear_input_box

def main():
    sample_text = "This is a live typing simulation using the human mimic function. Click into any text box where you want to see typing.. Typing test ready?"

    print("⌨️ Typing test ready.")
    print("👉 Click into any text box where you want to see typing.")
    print("👉 Press F8 to start typing, or ESC to cancel.")

    # Wait for F8
    keyboard.wait("f8")

    print("⌛ Starting in 2 seconds... focus the input box now!")
    time.sleep(2)

    # Clear the box first (optional)
    clear_input_box()
    time.sleep(0.3)

    # Type the sample text
    type_like_human(sample_text)

    print("✅ Done. Closing in 2 seconds...")
    time.sleep(2)

if __name__ == "__main__":
    main()