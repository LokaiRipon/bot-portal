# TODO: here we encrpyt your secret keys
import base64

# Your current keys
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjljNGI4YzdlMWYyMTRlYWRiY2YxNzNhZjg2NzZmZDVmIiwiaCI6Im11cm11cjY0In0="
DECRYPTION_KEY = b'SRDSMdmkLqb6i5s2Lqras6_HtiggxCSn08pzVXcWmTw='
ENCRYPTED_API_KEY = b'gAAAAABo7iRdrY9_uLboO-KneRg-G60yCsy3Q7TCPQIanl2TZ3jHo27Ra14GdpNZ7nKab7z-HaEiHHJ9VmDrM5uOB7Ma-bgOuVSe0J5i9c8jppahlnlnke1ctdby8S65hq3lH5curYKYriez4jMLsud4S5BJK-uGhqjwMl1OLe05iBQF2FkaEiVZ-XzGRopUDPiFoq1yuLNBybN22mV-TAJ3EZVSFRuHR30HiH_0KQ7aRByMMUbYZKixlb1k8-oE5jUQsXsbEKxw7FEkK9ucT7QwePCqVecmpeZX014k47-HbNkhsQfR1-E='
# TODO: These 3 keys are your actual Keys, so paste them here!
# Encode them 
ORS_API_KEY_B64 = base64.b64encode(ORS_API_KEY.encode()).decode()
DECRYPTION_KEY_B64 = base64.b64encode(DECRYPTION_KEY).decode()
ENCRYPTED_API_KEY_B64 = base64.b64encode(ENCRYPTED_API_KEY).decode()

print("ORS_API_KEY_B64 =", repr(ORS_API_KEY_B64))
print("DECRYPTION_KEY_B64 =", repr(DECRYPTION_KEY_B64))
print("ENCRYPTED_API_KEY_B64 =", repr(ENCRYPTED_API_KEY_B64)) # TODO: Copy this three results and place each in the config.py file!