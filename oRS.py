# TODO: here we encrpyt your secret keys
import base64

# Your current keys
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjljNGI4YzdlMWYyMTRlYWRiY2YxNzNhZjg2NzZmZDVmIiwiaCI6Im11cm11cjY0In0="
DECRYPTION_KEY = b'hJrITzKqFvmz1RapzLCVRIp7qoz5AFxnMusylrUt0zI='
ENCRYPTED_API_KEY = b'gAAAAABoy9upXALUshZA9NWTtZ7ATZWXuDIWXW6aKfZAHIwzB8Vd4-5fETx4YEduF2idjp-B-G3wGQjZrbv1jrbvtvlqBJ3k7yZLueJRgfGxgShclS4oy35NBzUIms6BV7ypWeomb9xtXSu6t_dm7ChBb2WW9ndBt2dL1-992r74kzzy6lr5sOw5Yhaq588mIM8SN0NsBdBqgWhwdSuLgmqKW18DsPCYGtAvt8ZSO-S0CXWRZW3r5sAviZC9DxXbHDPxZGxtvkP_3dKE-3OkMVKvwsNCpbWCrKWemrQzbZi7478_Kr3HzI0='
# TODO: These 3 keys are your actual Keys, so paste them here!
# Encode them 
ORS_API_KEY_B64 = base64.b64encode(ORS_API_KEY.encode()).decode()
DECRYPTION_KEY_B64 = base64.b64encode(DECRYPTION_KEY).decode()
ENCRYPTED_API_KEY_B64 = base64.b64encode(ENCRYPTED_API_KEY).decode()

print("ORS_API_KEY_B64 =", repr(ORS_API_KEY_B64))
print("DECRYPTION_KEY_B64 =", repr(DECRYPTION_KEY_B64))
print("ENCRYPTED_API_KEY_B64 =", repr(ENCRYPTED_API_KEY_B64)) # TODO: Copy this three results and place each in the config.py file!