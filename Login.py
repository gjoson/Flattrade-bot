import hashlib
import requests
import json

# ===== EDIT THESE =====
API_KEY = "971a4014f1984f0cbc85afacfd7816a9"
API_SECRET = "2026.b3bb2a8e05ab48099082a75ba8f4319518942c662cb31be2"
REDIRECT_URL = "https://auth.flattrade.in/?api_key=" + API_KEY

print("\nOpen this URL in browser and login:\n")
print(REDIRECT_URL)

print("\nAfter login you will be redirected to a URL like:")
print("https://...?code=XXXX&client=XXXXX")

code = input("\nPaste request_code here: ").strip()

raw = API_KEY + code + API_SECRET
sha256 = hashlib.sha256(raw.encode()).hexdigest()

payload = {
    "api_key": API_KEY,
    "request_code": code,
    "api_secret": sha256
}

r = requests.post(
    "https://authapi.flattrade.in/trade/apitoken",
    json=payload
)

data = r.json()
print("\nResponse:", data)

if data.get("stat") != "Ok":
    print("Login failed")
    exit()

session = {
    "client_id": data["actid"],
    "token": data["accesstoken"]
}

with open("session.json", "w") as f:
    json.dump(session, f)

print("\nSession saved to session.json")