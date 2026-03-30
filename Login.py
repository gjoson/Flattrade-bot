import hashlib
import requests
from urllib.parse import urlparse, parse_qs

API_KEY = "971a4014f1984f0cbc85afacfd7816a9"
API_SECRET = "2026.b3bb2a8e05ab48099082a75ba8f4319518942c662cb31be2"

print("\nOpen this URL and login:\n")
print(f"https://auth.flattrade.in/?api_key={API_KEY}")

print("\nAfter login you will be redirected to a URL like:")
print("https://something?code=XXXX&client=XXXX")

redirect_url = input("\nPaste the FULL redirect URL here:\n").strip()

parsed = urlparse(redirect_url)
params = parse_qs(parsed.query)

code = params["code"][0]
client = params["client"][0]

print("\nExtracted values:")
print("Code:", code)
print("Client:", client)

raw = API_KEY + code + API_SECRET
sha256 = hashlib.sha256(raw.encode()).hexdigest()

payload = {
    "api_key": API_KEY,
    "request_code": code,
    "api_secret": sha256
}

r = requests.post(
    "https://authapi.flattrade.in/trade/apitoken",
    data=payload
)

data = r.json()

token = data["access_token"]

with open("token.txt", "w") as f:
    f.write(f"{client}\n{token}")

print("\nToken saved to token.txt")