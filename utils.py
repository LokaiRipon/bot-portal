# utils.py (Example)
"""General utility functions used across the application."""
import uuid

def is_valid_uuid(uuid_string: str) -> bool:
    """Checks if a string is a valid UUID format."""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

def sanitize_input(user_input: str) -> str:
    """Basic sanitization to prevent injection or unexpected characters."""
    # Example: Strip leading/trailing whitespace
    return user_input.strip()
    # Add more rules as needed, but be careful not to break legitimate input

# encrypt_key.py
from cryptography.fernet import Fernet
import os

# 1. Generate a key for Fernet (This is the decryption key!)
#    You MUST keep this key safe. You will embed it in your main script.
decryption_key = Fernet.generate_key()
print("Decryption Key (KEEP THIS SAFE, needed for bot.py):")
print(decryption_key.decode()) # Print as string for easy copying

# with open("decryption_key.key", "wb") as key_file:
    # key_file.write(decryption_key)

# 3. Create a Fernet instance with the decryption key
fernet = Fernet(decryption_key)

# 4. The OpenAI API key you want to encrypt
api_key_to_encrypt = "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" # TODO: <--- CHANGE hapa to be your new API 

# 5. Encrypt the API key
encrypted_key = fernet.encrypt(api_key_to_encrypt.encode())

print("\nEncrypted API Key (Use this in bot.py):")
print(encrypted_key.decode()) # Print as string for easy copying

# with open("encrypted_api_key.key", "wb") as enc_file:
    # enc_file.write(encrypted_key)

print("\nKeys generated. Use the printed values in your bot.py.")
print("DO NOT share the Decryption Key!")